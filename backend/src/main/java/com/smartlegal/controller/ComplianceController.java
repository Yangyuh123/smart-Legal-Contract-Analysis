package com.smartlegal.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.PageResult;
import com.smartlegal.common.Result;
import com.smartlegal.service.ComplianceService;
import com.smartlegal.vo.ComplianceResultVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/compliance")
@RequiredArgsConstructor
@Tag(name = "合规检查", description = "合同合规性检查")
public class ComplianceController {

    private final ComplianceService complianceService;

    @PostMapping("/upload")
    @Operation(summary = "上传合同并执行合规检查")
    public Result<ComplianceResultVO> uploadAndCheck(
            @RequestParam("file") MultipartFile file,
            @RequestParam("complianceStandard") String complianceStandard,
            @RequestParam(value = "industry", required = false) String industry,
            @RequestParam(value = "jurisdiction", required = false) String jurisdiction) {
        return Result.success("合规检查完成", complianceService.check(file, complianceStandard, industry, jurisdiction));
    }

    @GetMapping("/{id}")
    @Operation(summary = "合规检查详情")
    public Result<ComplianceResultVO> getById(@PathVariable Long id) {
        return Result.success(complianceService.getById(id));
    }

    @GetMapping
    @Operation(summary = "合规检查历史")
    public Result<PageResult<ComplianceResultVO>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        Page<ComplianceResultVO> r = complianceService.listHistory(page, size);
        return Result.success(PageResult.of(r.getRecords(), r.getTotal(), r.getCurrent(), r.getSize()));
    }
}