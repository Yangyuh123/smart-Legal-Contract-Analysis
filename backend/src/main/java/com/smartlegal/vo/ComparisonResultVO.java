package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 合同比对结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ComparisonResultVO {

    /** 比对结果ID */
    private Long id;

    /** 合同A ID */
    private Long contractAId;

    /** 合同A标题 */
    private String contractATitle;

    /** 合同B ID */
    private Long contractBId;

    /** 合同B标题 */
    private String contractBTitle;

    /** 相似度百分比（0-100） */
    private Double similarity;

    /** 总差异数量 */
    private Integer totalDiffs;

    /** 比对时间 */
    private LocalDateTime createTime;

    /** 差异详情列表 */
    private List<DiffDetailVO> diffs;
}
