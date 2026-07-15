package com.smartlegal.service;

import com.smartlegal.dto.KnowledgeQueryDTO;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Flux;

import java.util.Map;

/**
 * 知识库服务接口
 */
public interface KnowledgeService {

    /**
     * 上传文档到知识库
     * @param file 文档文件
     * @param name 文档名称
     * @return 上传结果
     */
    Map<String, Object> uploadDoc(MultipartFile file, String title, String category);

    /**
     * 分页查询知识库文档列表
     * @param page 页码
     * @param size 每页大小
     * @return 文档列表
     */
    Map<String, Object> listDocs(int page, int size);

    /**
     * 知识问答（流式输出）
     * @param queryDTO 问题请求
     * @return SSE流式回答
     */
    Flux<String> qa(KnowledgeQueryDTO queryDTO);

    /**
     * 删除知识库文档
     * @param id 文档ID
     */
    void deleteDoc(Long id);

    /**
     * 重新索引所有已有文档到ChromaDB向量库
     * 用于修复向量库为空或数据不一致的情况
     * @return 重新索引结果
     */
    Map<String, Object> reindexAll();
}
