package com.smartlegal.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 合同生成消息DTO
 */
@Data
public class GenerationMessageDTO {

    /** 会话ID */
    @NotBlank(message = "会话ID不能为空")
    private String sessionId;

    /** 用户消息内容 */
    @NotBlank(message = "消息内容不能为空")
    private String content;
}
