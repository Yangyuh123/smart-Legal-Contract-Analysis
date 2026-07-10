package com.smartlegal.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.vo.ComparisonResultVO;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

public interface ComparisonService {
    ComparisonResultVO getById(Long id);
    Page<ComparisonResultVO> list(int page, int size);
    Map<String, Object> compareUpload(MultipartFile fileA, MultipartFile fileB, String reviewRequirements);
}
