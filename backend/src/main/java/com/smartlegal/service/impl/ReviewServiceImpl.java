package com.smartlegal.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.BusinessException;
import com.smartlegal.common.constants.ReviewStatus;
import com.smartlegal.entity.ReviewRecord;
import com.smartlegal.entity.ReviewRisk;
import com.smartlegal.mapper.ReviewRecordMapper;
import com.smartlegal.mapper.ReviewRiskMapper;
import com.smartlegal.service.NotificationService;
import com.smartlegal.service.ReviewService;
import com.smartlegal.vo.ReviewResultVO;
import com.smartlegal.vo.RiskItemVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.core.io.FileSystemResource;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReviewServiceImpl implements ReviewService {

    private final ReviewRecordMapper reviewRecordMapper;
    private final ReviewRiskMapper reviewRiskMapper;
    private final NotificationService notificationService;
    private final WebClient aiAgentWebClient;

    @Override
    public ReviewResultVO review(MultipartFile file, String reviewScope) {
        Long userId = getCurrentUserId();
        String filename = file.getOriginalFilename();

        // 1. 解析文件
        String textContent;
        try {
            Path tmp = Files.createTempDirectory("review_");
            File tmpFile = tmp.resolve(filename).toFile();
            file.transferTo(tmpFile);

            LinkedMultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
            parts.add("file", new FileSystemResource(tmpFile));
            @SuppressWarnings("unchecked")
            Map<String, Object> parseResult = aiAgentWebClient.post()
                    .uri("/ai/parse/upload").contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(parts)).retrieve().bodyToMono(Map.class).block();

            textContent = extractText(parseResult);
            tmpFile.delete(); Files.deleteIfExists(tmp);
        } catch (IOException e) { throw new BusinessException(500, "文件读取失败"); }

        if (textContent == null || textContent.isBlank())
            throw new BusinessException(400, "未能提取文本内容");

        // 2. 创建记录
        ReviewRecord record = new ReviewRecord();
        record.setUserId(userId); record.setFileName(filename);
        record.setContentText(textContent);
        record.setStatus(ReviewStatus.PROCESSING.name());
        record.setCreateTime(LocalDateTime.now());
        reviewRecordMapper.insert(record);

        // 3. 调用AI审查（同步等待）
        try {
            String scope = reviewScope != null ? reviewScope : "请全面审查本合同";
            Map<String, Object> body = Map.of("contract_text", textContent,
                    "contract_type", "", "review_requirements", scope);
            @SuppressWarnings("unchecked")
            Map<String, Object> aiResult = aiAgentWebClient.post()
                    .uri("/ai/review").bodyValue(body).retrieve().bodyToMono(Map.class).block();

            parseAndSaveRisks(record.getId(), aiResult, record);
            record.setStatus(ReviewStatus.COMPLETED.name());
            reviewRecordMapper.updateById(record);

            notificationService.createNotification(userId, "审查完成",
                    "文件 " + filename + " 审查完成，发现 " + record.getTotalRisks() + " 个风险项。",
                    "review_completed", record.getId());
            log.info("审查完成: id={}, risks={}", record.getId(), record.getTotalRisks());
        } catch (Exception e) {
            log.error("AI审查失败", e);
            record.setStatus(ReviewStatus.FAILED.name());
            record.setReviewSummary("审查失败: " + e.getMessage());
            reviewRecordMapper.updateById(record);
            throw new BusinessException(500, "审查失败: " + e.getMessage());
        }

        return getById(record.getId());
    }

    @Override
    public ReviewResultVO getById(Long id) {
        ReviewRecord record = reviewRecordMapper.selectById(id);
        if (record == null) throw new BusinessException(404, "审查记录不存在");
        List<ReviewRisk> risks = reviewRiskMapper.selectList(
                new LambdaQueryWrapper<ReviewRisk>().eq(ReviewRisk::getReviewId, id));
        List<RiskItemVO> vos = risks.stream().map(r -> RiskItemVO.builder()
                .id(r.getId()).riskLevel(r.getRiskLevel()).riskCategory(r.getRiskCategory())
                .riskTitle(r.getRiskTitle()).riskDescription(r.getRiskDescription())
                .riskPosition(r.getRiskPosition()).clauseSection(r.getClauseSection())
                .suggestion(r.getSuggestion()).suggestedText(r.getSuggestedText())
                .legalBasis(r.getLegalBasis()).build()).toList();
        return ReviewResultVO.builder().id(record.getId()).fileName(record.getFileName())
                .contentText(truncate(record.getContentText(), 8000)).contractTitle(record.getFileName())
                .status(record.getStatus()).totalRisks(record.getTotalRisks())
                .criticalRisks(record.getCriticalRisks()).generalRisks(record.getGeneralRisks())
                .lowRisks(record.getLowRisks()).reviewSummary(record.getReviewSummary())
                .createTime(record.getCreateTime()).risks(vos).build();
    }

    @Override
    public Page<ReviewResultVO> listHistory(int page, int size) {
        Long userId = getCurrentUserId();
        Page<ReviewRecord> rp = reviewRecordMapper.selectPage(Page.of(page, size),
                new LambdaQueryWrapper<ReviewRecord>().eq(ReviewRecord::getUserId, userId)
                        .orderByDesc(ReviewRecord::getCreateTime));
        Page<ReviewResultVO> vp = new Page<>(page, size, rp.getTotal());
        vp.setRecords(rp.getRecords().stream().map(r -> ReviewResultVO.builder()
                .id(r.getId()).fileName(r.getFileName()).contractTitle(r.getFileName())
                .status(r.getStatus()).totalRisks(r.getTotalRisks())
                .criticalRisks(r.getCriticalRisks()).generalRisks(r.getGeneralRisks())
                .lowRisks(r.getLowRisks()).reviewSummary(r.getReviewSummary())
                .createTime(r.getCreateTime()).build()).toList());
        return vp;
    }

    @Override
    public Object getStats() {
        Long userId = getCurrentUserId();
        List<ReviewRecord> all = reviewRecordMapper.selectList(
                new LambdaQueryWrapper<ReviewRecord>().eq(ReviewRecord::getUserId, userId));
        return Map.of("totalReviews", all.size(),
                "totalRisks", all.stream().mapToInt(r -> r.getTotalRisks() != null ? r.getTotalRisks() : 0).sum(),
                "criticalRisks", all.stream().mapToInt(r -> r.getCriticalRisks() != null ? r.getCriticalRisks() : 0).sum(),
                "generalRisks", all.stream().mapToInt(r -> r.getGeneralRisks() != null ? r.getGeneralRisks() : 0).sum(),
                "lowRisks", all.stream().mapToInt(r -> r.getLowRisks() != null ? r.getLowRisks() : 0).sum());
    }

    @Override
    public byte[] exportModified(Long id, String contentText, String format, String fileName) {
        if (contentText == null || contentText.isBlank()) {
            throw new BusinessException(400, "合同内容为空，无法导出");
        }
        try {
            if ("pdf".equalsIgnoreCase(format)) {
                return exportAsPdf(contentText, fileName);
            } else {
                return exportAsDocx(contentText, fileName);
            }
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("导出失败", e);
            throw new BusinessException(500, "导出失败: " + e.getMessage());
        }
    }

    private byte[] exportAsDocx(String contentText, String fileName) throws Exception {
        org.apache.poi.xwpf.usermodel.XWPFDocument doc = new org.apache.poi.xwpf.usermodel.XWPFDocument();

        // 添加标题
        org.apache.poi.xwpf.usermodel.XWPFParagraph titlePara = doc.createParagraph();
        titlePara.setAlignment(org.apache.poi.xwpf.usermodel.ParagraphAlignment.CENTER);
        org.apache.poi.xwpf.usermodel.XWPFRun titleRun = titlePara.createRun();
        String baseName = fileName.replaceAll("\\.[^.]+$", "");
        titleRun.setText(baseName);
        titleRun.setBold(true);
        titleRun.setFontSize(16);
        titleRun.setFontFamily("仿宋");

        // 添加空行
        doc.createParagraph();

        // 按段落添加内容
        String[] paragraphs = contentText.split("\n");
        for (String text : paragraphs) {
            String trimmed = text.trim();
            if (!trimmed.isEmpty()) {
                org.apache.poi.xwpf.usermodel.XWPFParagraph para = doc.createParagraph();
                para.setIndentationFirstLine(480); // 首行缩进2字符
                org.apache.poi.xwpf.usermodel.XWPFRun run = para.createRun();
                run.setText(trimmed);
                run.setFontSize(12);
                run.setFontFamily("仿宋");
            }
        }

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        doc.write(bos);
        doc.close();
        return bos.toByteArray();
    }

    private byte[] exportAsPdf(String contentText, String fileName) throws Exception {
        com.lowagie.text.Document document = new com.lowagie.text.Document(
                com.lowagie.text.PageSize.A4, 72, 72, 72, 72);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        com.lowagie.text.pdf.PdfWriter.getInstance(document, bos);

        document.open();

        // 标题
        String baseName = fileName.replaceAll("\\.[^.]+$", "");
        com.lowagie.text.Font titleFont = new com.lowagie.text.Font(
                com.lowagie.text.Font.HELVETICA, 16, com.lowagie.text.Font.BOLD);
        com.lowagie.text.Paragraph title = new com.lowagie.text.Paragraph(baseName, titleFont);
        title.setAlignment(com.lowagie.text.Element.ALIGN_CENTER);
        title.setSpacingAfter(20);
        document.add(title);

        // 内容段落
        com.lowagie.text.Font bodyFont = new com.lowagie.text.Font(
                com.lowagie.text.Font.HELVETICA, 11, com.lowagie.text.Font.NORMAL);
        String[] paragraphs = contentText.split("\n");
        for (String text : paragraphs) {
            String trimmed = text.trim();
            if (!trimmed.isEmpty()) {
                com.lowagie.text.Paragraph para = new com.lowagie.text.Paragraph(trimmed, bodyFont);
                para.setSpacingAfter(6);
                para.setFirstLineIndent(22);
                document.add(para);
            }
        }

        document.close();
        return bos.toByteArray();
    }

    @SuppressWarnings("unchecked")
    private void parseAndSaveRisks(Long reviewId, Map<String, Object> aiResult, ReviewRecord record) {
        if (aiResult == null) { record.setTotalRisks(0); return; }
        Map<String, Object> data = (Map<String, Object>) aiResult.get("data");
        if (data == null) data = aiResult;
        List<Map<String, Object>> risks = (List<Map<String, Object>>) data.getOrDefault("risk_items",
                data.getOrDefault("risks", List.of()));
        int c = 0, g = 0, l = 0;
        for (Map<String, Object> rd : risks) {
            ReviewRisk r = new ReviewRisk(); r.setReviewId(reviewId);
            r.setRiskLevel(String.valueOf(rd.getOrDefault("risk_level", "LOW")).toUpperCase());
            r.setRiskCategory((String) rd.getOrDefault("risk_category", ""));
            r.setRiskTitle((String) rd.getOrDefault("risk_title",
                    rd.getOrDefault("risk_category", "未分类风险")));
            r.setRiskDescription((String) rd.getOrDefault("risk_description", ""));
            r.setRiskPosition((String) rd.getOrDefault("original_text",
                    rd.getOrDefault("risk_position", "")));
            r.setClauseSection((String) rd.getOrDefault("clause_location",
                    rd.getOrDefault("clause_section", "")));
            r.setSuggestion((String) rd.getOrDefault("suggestion", ""));
            r.setSuggestedText((String) rd.getOrDefault("suggested_text", ""));
            r.setLegalBasis((String) rd.getOrDefault("legal_basis", ""));
            reviewRiskMapper.insert(r);
            switch (r.getRiskLevel()) { case "CRITICAL" -> c++; case "GENERAL" -> g++; default -> l++; }
        }
        record.setTotalRisks(risks.size()); record.setCriticalRisks(c);
        record.setGeneralRisks(g); record.setLowRisks(l);
        record.setReviewSummary((String) data.getOrDefault("overall_assessment", ""));
    }

    @SuppressWarnings("unchecked")
    private String extractText(Map<String, Object> r) {
        if (r == null) return "";
        Map<String, Object> d = (Map<String, Object>) r.get("data");
        if (d != null && d.get("full_text") != null) return (String) d.get("full_text");
        if (r.get("full_text") != null) return (String) r.get("full_text");
        return "";
    }

    private String truncate(String text, int maxLen) {
        if (text == null) return "";
        return text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }

    private Long getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) throw new BusinessException(401, "未登录");
        return (Long) auth.getPrincipal();
    }
}
