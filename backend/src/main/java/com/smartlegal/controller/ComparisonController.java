package com.smartlegal.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.PageResult;
import com.smartlegal.common.Result;
import com.smartlegal.service.ComparisonService;
import com.smartlegal.vo.ComparisonResultVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/comparisons")
@RequiredArgsConstructor
@Tag(name = "合同比对", description = "上传两份合同文件进行差异比对")
public class ComparisonController {

    private final ComparisonService comparisonService;

    @GetMapping
    @Operation(summary = "查询比对历史")
    public Result<PageResult<ComparisonResultVO>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Page<ComparisonResultVO> r = comparisonService.list(page, size);
        return Result.success(PageResult.of(r.getRecords(), r.getTotal(), r.getCurrent(), r.getSize()));
    }

    @GetMapping("/{id}")
    @Operation(summary = "比对详情")
    public Result<ComparisonResultVO> getById(@PathVariable Long id) {
        return Result.success(comparisonService.getById(id));
    }

    @PostMapping("/upload")
    @Operation(summary = "上传两份文件直接比对")
    public Result<Map<String, Object>> compareUpload(
            @RequestParam("fileA") MultipartFile fileA,
            @RequestParam("fileB") MultipartFile fileB,
            @RequestParam(value = "reviewRequirements", required = false) String reviewRequirements) {
        return Result.success("比对完成", comparisonService.compareUpload(fileA, fileB, reviewRequirements));
    }
}
