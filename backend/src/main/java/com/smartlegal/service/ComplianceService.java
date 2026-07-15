package com.smartlegal.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.vo.ComplianceResultVO;
import org.springframework.web.multipart.MultipartFile;

public interface ComplianceService {
    ComplianceResultVO check(MultipartFile file, String complianceStandard, String industry, String jurisdiction);
    ComplianceResultVO getById(Long id);
    Page<ComplianceResultVO> listHistory(int page, int size);
}