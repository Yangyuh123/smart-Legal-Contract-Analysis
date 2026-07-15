package com.smartlegal.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartlegal.entity.GenerationRecord;
import com.smartlegal.mapper.GenerationRecordMapper;
import com.smartlegal.service.GenerationService;
import com.smartlegal.service.NotificationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class GenerationServiceImpl implements GenerationService {

    private final WebClient aiAgentWebClient;
    private final GenerationRecordMapper generationRecordMapper;
    private final NotificationService notificationService;
    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public Flux<String> streamGenerate(Map<String, Object> request, Long userId) {
        String sessionId = UUID.randomUUID().toString();
        String contractType = (String) request.getOrDefault("contract_type", "其他");

        // 先保存完整内容用于收集
        StringBuilder collector = new StringBuilder();

        return aiAgentWebClient.post()
                .uri("/ai/generate/stream")
                .bodyValue(request)
                .retrieve()
                .bodyToFlux(String.class)
                .timeout(Duration.ofSeconds(180))
                .map(chunk -> {
                    // 收集内容：扫描每个 "content":"..." 片段
                    int idx = 0;
                    while ((idx = chunk.indexOf("\"content\"", idx)) >= 0) {
                        int start = chunk.indexOf("\"", idx + 11) + 1;
                        if (start <= 0) break;
                        int end = chunk.indexOf("\"", start);
                        if (end < 0) break;
                        collector.append(chunk, start, end);
                        idx = end + 1;
                    }
                    return chunk;
                })
                .doOnComplete(() -> {
                    String content = collector.toString().trim();
                    if (content.isBlank()) {
                        log.warn("生成内容为空，跳过保存。chunk分析: 未收集到content");
                        return;
                    }
                    try {
                        GenerationRecord rec = new GenerationRecord();
                        rec.setUserId(userId);
                        rec.setSessionId(sessionId);
                        rec.setContractType(contractType);
                        rec.setGeneratedContent(content);
                        rec.setStatus("draft");
                        rec.setCreateTime(LocalDateTime.now());
                        rec.setUpdateTime(LocalDateTime.now());
                        generationRecordMapper.insert(rec);
                        log.info("生成记录已保存: id={}, userId={}, len={}", rec.getId(), userId, content.length());
                        notificationService.createNotification(userId, "合同生成完成",
                                "已成功生成一份" + contractType + "合同", "generation", rec.getId());
                    } catch (Exception e) {
                        log.error("保存生成记录失败", e);
                    }
                })
                .onErrorResume(e -> Flux.just("data: [生成中断: " + e.getMessage() + "]\n\n"));
    }
}
