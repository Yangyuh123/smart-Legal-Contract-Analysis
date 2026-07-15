package com.smartlegal.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.BusinessException;
import com.smartlegal.common.constants.ComplianceStatus;
import com.smartlegal.entity.ComplianceRecord;
import com.smartlegal.entity.ComplianceIssue;
import com.smartlegal.mapper.ComplianceRecordMapper;
import com.smartlegal.mapper.ComplianceIssueMapper;
import com.smartlegal.service.ComplianceService;
import com.smartlegal.vo.ComplianceResultVO;
import com.smartlegal.vo.ComplianceIssueVO;
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
public class ComplianceServiceImpl implements ComplianceService {

    private final ComplianceRecordMapper complianceRecordMapper;
    private final ComplianceIssueMapper complianceIssueMapper;
    private final WebClient aiAgentWebClient;

    @Override
    public ComplianceResultVO check(MultipartFile file, String complianceStandard, String industry, String jurisdiction) {
        // 步骤1: 获取当前用户ID
        Long userId = getCurrentUserId();
        String filename = file.getOriginalFilename();

        // 步骤2: 解析文件（调用AI引擎 /ai/parse/upload）
        String textContent = parseFile(file, filename);

        // 步骤3: 创建合规检查记录（状态 PROCESSING）
        ComplianceRecord record = new ComplianceRecord();
        record.setUserId(userId);
        record.setFileName(filename);
        record.setContentText(textContent);
        record.setComplianceStandard(complianceStandard);
        record.setIndustry(industry != null ? industry : "未指定");
        record.setJurisdiction(jurisdiction != null ? jurisdiction : "中国大陆");
        record.setStatus(ComplianceStatus.PROCESSING.name());
        complianceRecordMapper.insert(record);

        // 步骤4: 调用AI合规检查（调用AI引擎 /ai/compliance）
        try {
            Map<String, Object> body = Map.of(
                    "contract_text", textContent,
                    "compliance_standard", complianceStandard,
                    "industry", record.getIndustry(),
                    "jurisdiction", record.getJurisdiction()
            );
            @SuppressWarnings("unchecked")
            Map<String, Object> aiResult = aiAgentWebClient.post()
                    .uri("/ai/compliance").bodyValue(body).retrieve().bodyToMono(Map.class).block();

            // 步骤5: 解析并保存合规问题
            parseAndSaveIssues(record.getId(), aiResult, record);
            
            // 步骤6: 更新记录状态为 COMPLETED
            record.setStatus(ComplianceStatus.COMPLETED.name());
            complianceRecordMapper.updateById(record);

            log.info("合规检查完成: id={}, issues={}", record.getId(), record.getTotalIssues());
        } catch (Exception e) {
            log.error("合规检查失败", e);
            record.setStatus(ComplianceStatus.FAILED.name());
            record.setSummary("检查失败: " + e.getMessage());
            complianceRecordMapper.updateById(record);
            throw new BusinessException(500, "合规检查失败: " + e.getMessage());
        }

        return getById(record.getId());
    }

    @Override
    public ComplianceResultVO getById(Long id) {
        ComplianceRecord record = complianceRecordMapper.selectById(id);
        if (record == null) throw new BusinessException(404, "合规检查记录不存在");
        
        List<ComplianceIssue> issues = complianceIssueMapper.selectByRecordId(id);
        List<ComplianceIssueVO> vos = issues.stream().map(i -> {
            ComplianceIssueVO vo = new ComplianceIssueVO();
            vo.setId(i.getId());
            vo.setIssueTitle(i.getIssueTitle());
            vo.setSeverity(i.getSeverity());
            vo.setClauseReference(i.getClauseReference());
            vo.setDescription(i.getDescription());
            vo.setLegalReference(i.getLegalReference());
            vo.setRecommendation(i.getRecommendation());
            vo.setPenaltyRisk(i.getPenaltyRisk());
            return vo;
        }).toList();

        ComplianceResultVO result = new ComplianceResultVO();
        result.setId(record.getId());
        result.setFileName(record.getFileName());
        result.setComplianceStandard(record.getComplianceStandard());
        result.setIndustry(record.getIndustry());
        result.setJurisdiction(record.getJurisdiction());
        result.setOverallCompliance(record.getOverallCompliance());
        result.setSummary(record.getSummary());
        result.setTotalIssues(record.getTotalIssues());
        result.setCriticalIssues(record.getCriticalIssues());
        result.setGeneralIssues(record.getGeneralIssues());
        result.setLowIssues(record.getLowIssues());
        result.setIssues(vos);
        result.setCreateTime(record.getCreateTime());
        return result;
    }

    @Override
    public Page<ComplianceResultVO> listHistory(int page, int size) {
        Long userId = getCurrentUserId();
        Page<ComplianceRecord> rp = complianceRecordMapper.selectPage(
                Page.of(page, size),
                new LambdaQueryWrapper<ComplianceRecord>()
                        .eq(ComplianceRecord::getUserId, userId)
                        .orderByDesc(ComplianceRecord::getCreateTime)
        );
        
        Page<ComplianceResultVO> vp = new Page<>(page, size, rp.getTotal());
        vp.setRecords(rp.getRecords().stream().map(r -> {
            ComplianceResultVO vo = new ComplianceResultVO();
            vo.setId(r.getId());
            vo.setFileName(r.getFileName());
            vo.setComplianceStandard(r.getComplianceStandard());
            vo.setOverallCompliance(r.getOverallCompliance());
            vo.setSummary(r.getSummary());
            vo.setTotalIssues(r.getTotalIssues());
            vo.setCriticalIssues(r.getCriticalIssues());
            vo.setGeneralIssues(r.getGeneralIssues());
            vo.setLowIssues(r.getLowIssues());
            vo.setCreateTime(r.getCreateTime());
            return vo;
        }).toList());
        return vp;
    }

    // ========== 辅助方法 ==========

    private String parseFile(MultipartFile file, String filename) {
        try {
            Path tmp = Files.createTempDirectory("compliance_");
            File tmpFile = tmp.resolve(filename).toFile();
            file.transferTo(tmpFile);

            LinkedMultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
            parts.add("file", new FileSystemResource(tmpFile));
            @SuppressWarnings("unchecked")
            Map<String, Object> parseResult = aiAgentWebClient.post()
                    .uri("/ai/parse/upload").contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(parts)).retrieve().bodyToMono(Map.class).block();

            String text = extractText(parseResult);
            tmpFile.delete();
            Files.deleteIfExists(tmp);
            return text;
        } catch (IOException e) {
            throw new BusinessException(500, "文件读取失败");
        }
    }

    @SuppressWarnings("unchecked")
    private String extractText(Map<String, Object> r) {
        if (r == null) return "";
        Map<String, Object> d = (Map<String, Object>) r.get("data");
        if (d != null && d.get("full_text") != null) return (String) d.get("full_text");
        if (r.get("full_text") != null) return (String) r.get("full_text");
        return "";
    }

    @SuppressWarnings("unchecked")
    private void parseAndSaveIssues(Long recordId, Map<String, Object> aiResult, ComplianceRecord record) {
        if (aiResult == null) {
            record.setTotalIssues(0);
            return;
        }
        Map<String, Object> data = (Map<String, Object>) aiResult.get("data");
        if (data == null) data = aiResult;
        
        List<Map<String, Object>> issues = (List<Map<String, Object>>) data.getOrDefault("issues", List.of());
        
        int critical = 0, general = 0, low = 0;
        for (Map<String, Object> issueData : issues) {
            ComplianceIssue issue = new ComplianceIssue();
            issue.setRecordId(recordId);
            issue.setIssueTitle((String) issueData.getOrDefault("issue_title", ""));
            issue.setSeverity(String.valueOf(issueData.getOrDefault("severity", "LOW")).toUpperCase());
            issue.setClauseReference((String) issueData.getOrDefault("clause_reference", ""));
            issue.setDescription((String) issueData.getOrDefault("description", ""));
            issue.setLegalReference((String) issueData.getOrDefault("legal_reference", ""));
            issue.setRecommendation((String) issueData.getOrDefault("recommendation", ""));
            issue.setPenaltyRisk((String) issueData.getOrDefault("penalty_risk", ""));
            complianceIssueMapper.insert(issue);
            
            switch (issue.getSeverity()) {
                case "CRITICAL" -> critical++;
                case "GENERAL" -> general++;
                default -> low++;
            }
        }
        
        record.setTotalIssues(issues.size());
        record.setCriticalIssues(critical);
        record.setGeneralIssues(general);
        record.setLowIssues(low);
        record.setOverallCompliance((String) data.getOrDefault("overall_compliance", "unknown"));
        record.setSummary((String) data.getOrDefault("summary", "合规检查完成"));
    }

    private Long getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            throw new BusinessException(401, "未登录");
        }
        return (Long) auth.getPrincipal();
    }
}