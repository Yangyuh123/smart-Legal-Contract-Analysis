package com.smartlegal.controller;

import com.smartlegal.common.Result;
import com.smartlegal.dto.KnowledgeQueryDTO;
import com.smartlegal.security.JwtTokenProvider;
import com.smartlegal.service.KnowledgeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Flux;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/knowledge")
@RequiredArgsConstructor
@Tag(name = "知识库", description = "知识文档管理与RAG智能问答")
public class KnowledgeController {

    private final KnowledgeService knowledgeService;
    private final JwtTokenProvider jwtTokenProvider;

    @PostMapping("/documents")
    @Operation(summary = "上传知识文档")
    public Result<Map<String, Object>> uploadDoc(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "title", required = false) String title,
            @RequestParam(value = "category", required = false) String category) {
        return Result.success("上传成功", knowledgeService.uploadDoc(file, title, category));
    }

    @GetMapping("/documents")
    @Operation(summary = "文档列表")
    public Result<Map<String, Object>> listDocs(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return Result.success(knowledgeService.listDocs(page, size));
    }

    @DeleteMapping("/documents/{id}")
    @Operation(summary = "删除文档")
    public Result<Void> deleteDoc(@PathVariable Long id) {
        knowledgeService.deleteDoc(id);
        return Result.ok("删除成功");
    }

    @PostMapping("/reindex")
    @Operation(summary = "重新索引所有文档到向量库")
    public Result<Map<String, Object>> reindexAll() {
        return Result.success("重新索引完成", knowledgeService.reindexAll());
    }

    @PostMapping(value = "/qa", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "RAG智能问答(SSE流式)")
    public Flux<String> qa(@Valid @RequestBody KnowledgeQueryDTO queryDTO, HttpServletRequest httpRequest) {
        // 手动验证JWT（SSE async dispatch会丢失SecurityContext，因此此接口在SecurityConfig中设为permitAll）
        String token = extractToken(httpRequest);
        if (token == null || !jwtTokenProvider.validateToken(token)) {
            return Flux.error(new org.springframework.security.access.AccessDeniedException("未授权访问"));
        }
        return knowledgeService.qa(queryDTO);
    }

    private String extractToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
