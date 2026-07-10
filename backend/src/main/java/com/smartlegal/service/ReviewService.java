package com.smartlegal.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.vo.ReviewResultVO;
import org.springframework.web.multipart.MultipartFile;

public interface ReviewService {
    /** 上传并审查，同步等待结果 */
    ReviewResultVO review(MultipartFile file, String reviewScope);
    ReviewResultVO getById(Long id);
    Page<ReviewResultVO> listHistory(int page, int size);
    Object getStats();
    /** 导出修改后的合同文件 */
    byte[] exportModified(Long id, String contentText, String format, String fileName);
}
