package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 风险项VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RiskItemVO {

    /** 风险ID */
    private Long id;

    /** 风险等级：CRITICAL-重大风险、GENERAL-一般风险、LOW-低风险 */
    private String riskLevel;

    /** 风险类别 */
    private String riskCategory;

    /** 风险标题 */
    private String riskTitle;

    /** 风险描述 */
    private String riskDescription;

    /** 风险位置（原文片段） */
    private String riskPosition;

    /** 条款章节 */
    private String clauseSection;

    /** 修改建议 */
    private String suggestion;

    /** 建议修改后的文本 */
    private String suggestedText;

    /** 法律依据 */
    private String legalBasis;
}
