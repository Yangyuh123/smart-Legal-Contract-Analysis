package com.smartlegal.vo;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;

@Data
public class ComplianceResultVO {
    private Long id;
    private String fileName;
    private String complianceStandard;
    private String industry;
    private String jurisdiction;
    private String overallCompliance;
    private String summary;
    private Integer totalIssues;
    private Integer criticalIssues;
    private Integer generalIssues;
    private Integer lowIssues;
    private List<ComplianceIssueVO> issues;
    private LocalDateTime createTime;
}