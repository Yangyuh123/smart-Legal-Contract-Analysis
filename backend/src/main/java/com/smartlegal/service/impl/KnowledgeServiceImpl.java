package com.smartlegal.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.BusinessException;
import com.smartlegal.dto.KnowledgeQueryDTO;
import com.smartlegal.entity.KbDocument;
import com.smartlegal.mapper.KbDocumentMapper;
import com.smartlegal.service.KnowledgeService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class KnowledgeServiceImpl implements KnowledgeService {

    private final WebClient aiAgentWebClient;
    private final KbDocumentMapper kbDocumentMapper;
    private static final Path UPLOAD_DIR = Path.of(System.getProperty("user.dir"), "uploads", "knowledge");

    static {
        try { Files.createDirectories(UPLOAD_DIR); } catch (IOException ignored) {}
    }

    @Override
    public Map<String, Object> uploadDoc(MultipartFile file, String title, String category) {
        try {
            // 1. 保存文件到本地
            String filename = UUID.randomUUID().toString().substring(0, 8) + "_" + file.getOriginalFilename();
            Path dest = UPLOAD_DIR.resolve(filename);
            file.transferTo(dest.toFile());

            // 2. 调 FastAPI 索引到 ChromaDB
            @SuppressWarnings("unchecked")
            Map<String, Object> resp = aiAgentWebClient.post()
                    .uri("/ai/knowledge/index")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(Map.of(
                            "file_paths", java.util.List.of(dest.toAbsolutePath().toString()),
                            "collection_name", "legal_knowledge"))
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            // 3. 解析FastAPI响应并写入MySQL
            int chunkCount = 0;
            if (resp != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> data = (Map<String, Object>) resp.get("data");
                if (data != null) {
                    Object c = data.get("chunks_indexed");
                    if (c instanceof Integer) chunkCount = (Integer) c;
                    else if (c instanceof Number) chunkCount = ((Number) c).intValue();
                }
            }

            KbDocument doc = new KbDocument();
            doc.setTitle(title != null ? title : file.getOriginalFilename());
            doc.setCategory(category);
            doc.setSource(dest.toAbsolutePath().toString());
            doc.setContent("");
            doc.setChunkCount(chunkCount);
            // 状态：分块数>0才是真正索引成功
            doc.setStatus(chunkCount > 0 ? 1 : 0);
            kbDocumentMapper.insert(doc);

            log.info("知识库文档已保存: id={}, title={}", doc.getId(), doc.getTitle());
            return Map.of("id", doc.getId(), "title", doc.getTitle());

        } catch (IOException e) {
            log.error("上传失败", e);
            throw new BusinessException(500, "上传失败: " + e.getMessage());
        }
    }

    @Override
    public Map<String, Object> listDocs(int page, int size) {
        Page<KbDocument> result = kbDocumentMapper.selectPage(
                Page.of(page, size),
                new LambdaQueryWrapper<KbDocument>().orderByDesc(KbDocument::getCreateTime));
        return Map.of("records", result.getRecords(), "total", result.getTotal());
    }

    @Override
    public Flux<String> qa(KnowledgeQueryDTO queryDTO) {
        log.info("知识库问答开始: question='{}'", queryDTO.getQuestion());
        return aiAgentWebClient.post()
                .uri("/ai/knowledge/qa")
                .bodyValue(Map.of("question", queryDTO.getQuestion()))
                .retrieve()
                .bodyToFlux(String.class)
                .timeout(Duration.ofSeconds(120))
                .onErrorResume(e -> {
                    log.error("知识库问答中断: {}", e.getMessage(), e);
                    return Flux.just("data: {\"error\":\"" + e.getMessage().replace("\"", "'") + "\"}\n\n",
                                     "data: [DONE]\n\n");
                });
    }

    @Override
    public void deleteDoc(Long id) {
        KbDocument doc = kbDocumentMapper.selectById(id);
        if (doc == null) throw new BusinessException(404, "文档不存在");
        // 删除本地文件
        try { Files.deleteIfExists(Path.of(doc.getSource())); } catch (IOException ignored) {}
        // 删除数据库记录
        kbDocumentMapper.deleteById(id);
    }

    @Override
    public Map<String, Object> reindexAll() {
        // 1. 查询所有已启用的文档
        List<KbDocument> docs = kbDocumentMapper.selectList(
                new LambdaQueryWrapper<KbDocument>().eq(KbDocument::getStatus, 1));

        if (docs.isEmpty()) {
            return Map.of("status", "no_docs", "message", "没有可重新索引的文档", "total_docs", 0);
        }

        // 2. 收集所有文件路径（只索引文件实际存在的）
        List<String> filePaths = docs.stream()
                .map(KbDocument::getSource)
                .filter(path -> {
                    try { return Files.exists(Path.of(path)); }
                    catch (Exception e) { return false; }
                })
                .toList();

        if (filePaths.isEmpty()) {
            return Map.of("status", "no_files", "message", "没有可访问的文档文件", "total_docs", docs.size());
        }

        // 3. 调用 FastAPI 重新索引
        @SuppressWarnings("unchecked")
        Map<String, Object> resp = aiAgentWebClient.post()
                .uri("/ai/knowledge/index")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(Map.of(
                        "file_paths", filePaths,
                        "collection_name", "legal_knowledge"))
                .retrieve()
                .bodyToMono(Map.class)
                .block(Duration.ofSeconds(120));

        // 4. 解析响应并更新MySQL中的chunk_count
        int totalChunks = 0;
        if (resp != null) {
            @SuppressWarnings("unchecked")
            Map<String, Object> data = (Map<String, Object>) resp.get("data");
            if (data != null) {
                Object c = data.get("chunks_indexed");
                if (c instanceof Integer) totalChunks = (Integer) c;
                else if (c instanceof Number) totalChunks = ((Number) c).intValue();
            }
        }

        // 5. 更新所有文档的chunk_count
        for (KbDocument doc : docs) {
            doc.setChunkCount(totalChunks > 0 ? Math.max(1, totalChunks / docs.size()) : 0);
            doc.setStatus(totalChunks > 0 ? 1 : 0);
            kbDocumentMapper.updateById(doc);
        }

        log.info("重新索引完成: {} 个文档, {} 个文本块", filePaths.size(), totalChunks);
        return Map.of(
                "status", "success",
                "message", "重新索引完成",
                "total_docs", docs.size(),
                "indexed_files", filePaths.size(),
                "total_chunks", totalChunks
        );
    }
}
