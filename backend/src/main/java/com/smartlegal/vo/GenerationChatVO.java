package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 合同生成对话VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GenerationChatVO {

    /** 会话ID */
    private String sessionId;

    /** 会话标题 */
    private String title;

    /** 会话状态：active-进行中、finalized-已定稿 */
    private String status;

    /** 对话消息列表 */
    private List<ChatMessage> messages;

    /** 创建时间 */
    private LocalDateTime createTime;

    /**
     * 对话消息
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatMessage {
        /** 消息角色：user-用户、assistant-助手 */
        private String role;

        /** 消息内容 */
        private String content;

        /** 消息时间 */
        private LocalDateTime time;
    }
}
