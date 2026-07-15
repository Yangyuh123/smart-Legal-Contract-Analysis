package com.smartlegal.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("compliance_record")
public class ComplianceRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String fileName;
    private String contentText;
    private String complianceStandard;
    private String industry;
    private String jurisdiction;
    private String overallCompliance;
    private String summary;
    private Integer totalIssues;
    private Integer criticalIssues;
    private Integer generalIssues;
    private Integer lowIssues;
    private String status;
    
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}