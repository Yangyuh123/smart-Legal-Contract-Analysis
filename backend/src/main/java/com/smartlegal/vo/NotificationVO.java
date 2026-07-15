package com.smartlegal.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 通知消息VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationVO {

    /** 通知ID */
    private Long id;

    /** 通知标题 */
    private String title;

    /** 通知内容 */
    private String content;

    /** 通知类型：review_completed-审查完成、risk_alert-风险预警、system-系统通知 */
    private String type;

    /** 关联业务ID */
    private Long relatedId;

    /** 是否已读：0-未读，1-已读 */
    private Integer isRead;

    /** 创建时间 */
    private LocalDateTime createTime;
}
