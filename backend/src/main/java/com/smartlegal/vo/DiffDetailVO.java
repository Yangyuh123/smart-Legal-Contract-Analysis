package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 差异详情VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DiffDetailVO {

    /** 差异类型：added-新增、deleted-删除、modified-修改 */
    private String diffType;

    /** 合同A中的原文内容 */
    private String contentA;

    /** 合同B中的原文内容 */
    private String contentB;

    /** 条款章节位置 */
    private String clauseSection;

    /** 差异描述/说明 */
    private String description;
}
