package com.smartlegal.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.vo.NotificationVO;

import java.util.Map;

/**
 * 通知服务接口
 */
public interface NotificationService {

    /**
     * 分页查询当前用户的通知列表
     * @param page 页码
     * @param size 每页大小
     * @return 分页通知列表
     */
    Page<NotificationVO> list(int page, int size);

    /**
     * 标记单条通知为已读
     * @param id 通知ID
     */
    void read(Long id);

    /**
     * 标记所有通知为已读
     */
    void readAll();

    /**
     * 获取当前用户的未读通知数量
     * @return 未读数量
     */
    Map<String, Object> unreadCount();

    /**
     * 创建一条通知
     * @param userId 接收用户ID
     * @param title 标题
     * @param content 内容
     * @param type 类型
     * @param relatedId 关联业务ID
     */
    void createNotification(Long userId, String title, String content, String type, Long relatedId);
}
