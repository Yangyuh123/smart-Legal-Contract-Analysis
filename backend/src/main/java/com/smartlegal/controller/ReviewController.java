package com.smartlegal.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.PageResult;
import com.smartlegal.common.Result;
import com.smartlegal.service.ReviewService;
import com.smartlegal.vo.ReviewResultVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/reviews")
@RequiredArgsConstructor
@Tag(name = "智能审查", description = "上传合同文件，AI审查法律风险")
public class ReviewController {

    private final ReviewService reviewService;

    @PostMapping("/upload")
    @Operation(summary = "上传合同并执行AI审查（同步等待结果）")
    public Result<ReviewResultVO> uploadAndReview(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "reviewScope", required = false) String reviewScope) {
        return Result.success("审查完成", reviewService.review(file, reviewScope));
    }

    @GetMapping
    @Operation(summary = "审查历史")
    public Result<PageResult<ReviewResultVO>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Page<ReviewResultVO> r = reviewService.listHistory(page, size);
        return Result.success(PageResult.of(r.getRecords(), r.getTotal(), r.getCurrent(), r.getSize()));
    }

    @GetMapping("/{id}")
    @Operation(summary = "审查详情")
    public Result<ReviewResultVO> getById(@PathVariable Long id) {
        return Result.success(reviewService.getById(id));
    }

    @GetMapping("/stats")
    @Operation(summary = "审查统计")
    public Result<Object> stats() {
        return Result.success(reviewService.getStats());
    }

    @PostMapping("/{id}/export")
    @Operation(summary = "导出修改后的合同文件")
    public ResponseEntity<byte[]> exportModified(
            @PathVariable Long id,
            @RequestBody Map<String, String> body) {
        String format = body.getOrDefault("format", "docx");
        String contentText = body.getOrDefault("contentText", "");
        String fileName = body.getOrDefault("fileName", "contract");

        byte[] fileBytes = reviewService.exportModified(id, contentText, format, fileName);

        String mimeType = "pdf".equals(format)
                ? "application/pdf"
                : "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
        String ext = "pdf".equals(format) ? ".pdf" : ".docx";
        String baseName = fileName.replaceAll("\\.[^.]+$", "");

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + baseName + "_modified" + ext + "\"")
                .contentType(MediaType.parseMediaType(mimeType))
                .body(fileBytes);
    }
}
