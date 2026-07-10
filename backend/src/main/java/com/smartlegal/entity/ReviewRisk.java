package com.smartlegal.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("review_risk")
public class ReviewRisk {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long reviewId;
    private String riskLevel;
    private String riskCategory;
    private String riskTitle;
    private String riskDescription;
    private String riskPosition;
    private String clauseSection;
    private String suggestion;
    private String suggestedText;
    private String legalBasis;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
