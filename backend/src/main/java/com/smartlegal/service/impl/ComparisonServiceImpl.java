package com.smartlegal.service.impl;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.BusinessException;
import com.smartlegal.service.ComparisonService;
import com.smartlegal.service.NotificationService;
import com.smartlegal.vo.ComparisonResultVO;
import com.smartlegal.vo.DiffDetailVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Slf4j
@Service
@RequiredArgsConstructor
public class ComparisonServiceImpl implements ComparisonService {

    private final WebClient aiAgentWebClient;
    private final NotificationService notificationService;
    private final Map<Long, ComparisonResultVO> store = new ConcurrentHashMap<>();
    private final AtomicLong idGen = new AtomicLong(1);

    @Override
    public ComparisonResultVO getById(Long id) {
        ComparisonResultVO r = store.get(id);
        if (r == null) throw new BusinessException(404, "比对记录不存在");
        return r;
    }

    @Override
    public Page<ComparisonResultVO> list(int page, int size) {
        var all = store.values().stream()
                .sorted((a, b) -> b.getCreateTime().compareTo(a.getCreateTime())).toList();
        int from = Math.min((page - 1) * size, all.size());
        int to = Math.min(from + size, all.size());
        Page<ComparisonResultVO> p = new Page<>(page, size, all.size());
        p.setRecords(from < all.size() ? all.subList(from, to) : List.of());
        return p;
    }

    @Override
    @SuppressWarnings("unchecked")
    public Map<String, Object> compareUpload(MultipartFile fileA, MultipartFile fileB, String reviewRequirements) {
        try {
            // 1. 保存临时文件
            Path tmp = Files.createTempDirectory("cmp_");
            File fa = tmp.resolve("a_" + fileA.getOriginalFilename()).toFile();
            File fb = tmp.resolve("b_" + fileB.getOriginalFilename()).toFile();
            fileA.transferTo(fa);
            fileB.transferTo(fb);

            // 2. 调用FastAPI解析文件（用 LinkedMultiValueMap + BodyInserters）
            String ta = parseFile(fa, fileA.getOriginalFilename());
            String tb = parseFile(fb, fileB.getOriginalFilename());

            // 清理临时文件
            try { fa.delete(); fb.delete(); Files.deleteIfExists(tmp); } catch (Exception ignored) {}

            if (ta.isBlank() || tb.isBlank()) {
                throw new BusinessException(400, "未能从文件中提取文本内容，请确保文件包含可读文字");
            }

            log.info("文件A: {} ({}字), 文件B: {} ({}字)", fileA.getOriginalFilename(), ta.length(), fileB.getOriginalFilename(), tb.length());

            // 3. 调用AI比对（附带审查要求）
            // 将审查要求前置到文本中让AI感知
            String oText = ta;
            String rText = tb;
            if (reviewRequirements != null && !reviewRequirements.isBlank()) {
                oText = "【比对重点：" + reviewRequirements + "】\n" + ta;
                rText = "【比对重点：" + reviewRequirements + "】\n" + tb;
            }
            Map<String, Object> aiBody = Map.of(
                    "original_text", oText,
                    "revised_text", rText,
                    "compare_mode", "detailed");

            Map<String, Object> aiResp = aiAgentWebClient.post().uri("/ai/compare")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(aiBody)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            // 4. 解析AI响应
            Map<String, Object> aiData = (Map<String, Object>) aiResp.get("data");
            if (aiData == null) aiData = aiResp;

            List<Map<String, Object>> diffsRaw = (List<Map<String, Object>>) aiData.getOrDefault("diffs", List.of());
            List<DiffDetailVO> diffVOs = diffsRaw.stream().map(d -> DiffDetailVO.builder()
                    .diffType((String) d.getOrDefault("diff_type", "modification"))
                    .contentA((String) d.getOrDefault("original_content", ""))
                    .contentB((String) d.getOrDefault("revised_content", ""))
                    .clauseSection((String) d.getOrDefault("clause_location", ""))
                    .description((String) d.getOrDefault("change_description", ""))
                    .build()).toList();

            // 5. 提取相似度，如果AI返回0则Java兜底计算
            Double similarity = 0.0;
            Object simObj = aiData.get("similarity");
            if (simObj instanceof Number) {
                similarity = ((Number) simObj).doubleValue();
            }
            if (similarity <= 0.0) {
                // 兜底：Java本地计算 difflib 相似度
                similarity = computeSimilarity(ta, tb);
            }
            log.info("比对完成: similarity={}%, diffs={}", similarity, diffVOs.size());

            // 6. 存入内存
            long id = idGen.getAndIncrement();
            ComparisonResultVO vo = ComparisonResultVO.builder()
                    .id(id).createTime(LocalDateTime.now())
                    .contractATitle(fileA.getOriginalFilename())
                    .contractBTitle(fileB.getOriginalFilename())
                    .similarity(similarity).totalDiffs(diffVOs.size()).diffs(diffVOs).build();
            store.put(id, vo);
            notificationService.createNotification(1L, "比对完成",
                    "合同比对完成，相似度 " + String.format("%.1f", similarity) + "%", "comparison", id);

            return Map.of("compareId", id, "similarity", similarity, "diffs", diffVOs);

        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("比对失败", e);
            throw new BusinessException(500, "文件比对失败: " + e.getMessage());
        }
    }

    /** 调用FastAPI解析文件，返回文本内容 */
    @SuppressWarnings("unchecked")
    private String parseFile(File file, String filename) {
        // 如果是纯文本文件，直接读
        String lower = filename.toLowerCase();
        if (lower.endsWith(".txt") || lower.endsWith(".md")) {
            try { return Files.readString(file.toPath()); } catch (Exception e) { return ""; }
        }

        // PDF/Word 调用FastAPI解析
        try {
            LinkedMultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
            parts.add("file", new FileSystemResource(file));

            Map<String, Object> resp = aiAgentWebClient.post()
                    .uri("/ai/parse/upload")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(parts))
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            if (resp == null) return "";
            Map<String, Object> data = (Map<String, Object>) resp.get("data");
            if (data != null && data.get("full_text") != null) return (String) data.get("full_text");
            if (resp.get("full_text") != null) return (String) resp.get("full_text");
            return "";
        } catch (Exception e) {
            log.error("FastAPI解析失败，尝试直接读文本: {}", e.getMessage());
            try { return Files.readString(file.toPath()); } catch (Exception ex) { return ""; }
        }
    }

    /** 本地计算文本相似度（兜底方案） */
    private double computeSimilarity(String a, String b) {
        if (a == null || b == null || a.isEmpty() || b.isEmpty()) return 0.0;
        // 按字符分割，计算共有字符比例
        Set<String> setA = new HashSet<>();
        for (int i = 0; i < a.length() - 1; i++) setA.add(a.substring(i, i + 2));
        Set<String> setB = new HashSet<>();
        for (int i = 0; i < b.length() - 1; i++) setB.add(b.substring(i, i + 2));

        Set<String> intersection = new HashSet<>(setA);
        intersection.retainAll(setB);
        Set<String> union = new HashSet<>(setA);
        union.addAll(setB);

        if (union.isEmpty()) return 100.0;
        return Math.round(intersection.size() * 10000.0 / union.size()) / 100.0;
    }
}
