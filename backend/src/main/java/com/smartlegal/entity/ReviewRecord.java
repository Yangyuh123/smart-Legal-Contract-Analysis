package com.smartlegal.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("review_record")
public class ReviewRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String fileName;
    private String contentText;
    private Long userId;
    private String status;
    private Integer totalRisks;
    private Integer criticalRisks;
    private Integer generalRisks;
    private Integer lowRisks;
    private String reviewSummary;
    private String aiModel;
    private Integer processingTime;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
