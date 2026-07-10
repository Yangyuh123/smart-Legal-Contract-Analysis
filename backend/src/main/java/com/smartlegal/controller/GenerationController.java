package com.smartlegal.controller;

import com.smartlegal.security.JwtTokenProvider;
import com.smartlegal.service.GenerationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;

/**
 * 合同生成控制器 — SSE代理到FastAPI
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/generation")
@RequiredArgsConstructor
@Tag(name = "合同生成", description = "AI流式生成合同")
public class GenerationController {

    private final GenerationService generationService;
    private final JwtTokenProvider jwtTokenProvider;

    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "流式生成合同")
    public Flux<String> streamGenerate(
            @RequestBody Map<String, Object> request,
            HttpServletRequest httpRequest) {

        // 手动验证JWT（SSE async dispatch会丢失SecurityContext，因此此接口在SecurityConfig中设为permitAll）
        String token = extractToken(httpRequest);
        if (token == null || !jwtTokenProvider.validateToken(token)) {
            return Flux.error(new org.springframework.security.access.AccessDeniedException("未授权访问"));
        }

        Long userId = jwtTokenProvider.getUserId(token);
        // 前端 camelCase → FastAPI snake_case
        if (request.containsKey("contractType")) {
            request.put("contract_type", request.remove("contractType"));
        }
        if (request.containsKey("partyA")) {
            request.put("party_a", request.remove("partyA"));
        }
        if (request.containsKey("partyB")) {
            request.put("party_b", request.remove("partyB"));
        }
        return generationService.streamGenerate(request, userId);
    }

    private String extractToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
