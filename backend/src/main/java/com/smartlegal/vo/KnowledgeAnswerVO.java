package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 知识库问答回答VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KnowledgeAnswerVO {

    /** 问题 */
    private String question;

    /** 回答内容 */
    private String answer;

    /** 引用来源列表 */
    private List<Citation> citations;

    /** 置信度（0-1） */
    private Double confidence;

    /**
     * 引用来源
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Citation {
        /** 文档ID */
        private Long documentId;

        /** 文档名称 */
        private String documentName;

        /** 引用片段 */
        private String snippet;

        /** 引用页码或位置 */
        private String location;
    }
}
