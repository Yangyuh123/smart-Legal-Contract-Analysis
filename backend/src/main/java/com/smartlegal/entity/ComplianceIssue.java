package com.smartlegal.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

@Data
@TableName("compliance_issue")
public class ComplianceIssue {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long recordId;
    private String issueTitle;
    private String severity;
    private String clauseReference;
    private String description;
    private String legalReference;
    private String recommendation;
    private String penaltyRisk;
}