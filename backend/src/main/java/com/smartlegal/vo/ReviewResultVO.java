package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 审查结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewResultVO {

    /** 审查记录ID */
    private Long id;

    /** 审查文件名 */
    private String fileName;

    /** 文件全文内容 */
    private String contentText;

    /** 审查标题 */
    private String contractTitle;

    /** 审查状态 */
    private String status;

    /** 风险总数 */
    private Integer totalRisks;

    /** 重大风险数 */
    private Integer criticalRisks;

    /** 一般风险数 */
    private Integer generalRisks;

    /** 低风险数 */
    private Integer lowRisks;

    /** 审查摘要 */
    private String reviewSummary;

    /** 使用的AI模型 */
    private String aiModel;

    /** 处理耗时（秒） */
    private Integer processingTime;

    /** 审查时间 */
    private LocalDateTime createTime;

    /** 所有风险项列表 */
    private List<RiskItemVO> risks;
}
