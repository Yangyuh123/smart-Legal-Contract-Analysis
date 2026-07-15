package com.smartlegal.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 知识库问答请求DTO
 */
@Data
public class KnowledgeQueryDTO {

    /** 用户问题 */
    @NotBlank(message = "问题不能为空")
    private String question;
}
