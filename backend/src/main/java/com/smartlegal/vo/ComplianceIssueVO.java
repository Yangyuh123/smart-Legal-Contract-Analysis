package com.smartlegal.vo;

import lombok.Data;

@Data
public class ComplianceIssueVO {
    private Long id;
    private String issueTitle;
    private String severity;
    private String clauseReference;
    private String description;
    private String legalReference;
    private String recommendation;
    private String penaltyRisk;
}