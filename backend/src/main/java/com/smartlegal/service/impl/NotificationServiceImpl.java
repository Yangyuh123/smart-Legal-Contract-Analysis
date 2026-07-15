package com.smartlegal.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.BusinessException;
import com.smartlegal.entity.Notification;
import com.smartlegal.mapper.NotificationMapper;
import com.smartlegal.service.NotificationService;
import com.smartlegal.vo.NotificationVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;

/**
 * 通知服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationServiceImpl implements NotificationService {

    private final NotificationMapper notificationMapper;

    @Override
    public Page<NotificationVO> list(int page, int size) {
        Long userId = getCurrentUserId();
        LambdaQueryWrapper<Notification> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Notification::getUserId, userId)
               .orderByDesc(Notification::getCreateTime);

        Page<Notification> pageResult = notificationMapper.selectPage(Page.of(page, size), wrapper);

        Page<NotificationVO> voPage = new Page<>(page, size, pageResult.getTotal());
        List<NotificationVO> voList = pageResult.getRecords().stream()
                .map(this::convertToVO)
                .toList();
        voPage.setRecords(voList);
        return voPage;
    }

    @Override
    @Transactional
    public void read(Long id) {
        Notification notification = notificationMapper.selectById(id);
        if (notification == null) {
            throw new BusinessException(404, "通知不存在");
        }
        notification.setIsRead(1);
        notificationMapper.updateById(notification);
    }

    @Override
    @Transactional
    public void readAll() {
        Long userId = getCurrentUserId();
        LambdaUpdateWrapper<Notification> wrapper = new LambdaUpdateWrapper<>();
        wrapper.eq(Notification::getUserId, userId)
               .eq(Notification::getIsRead, 0)
               .set(Notification::getIsRead, 1);
        notificationMapper.update(null, wrapper);
        log.info("用户 {} 的所有通知已标记为已读", userId);
    }

    @Override
    public Map<String, Object> unreadCount() {
        Long userId = getCurrentUserId();
        LambdaQueryWrapper<Notification> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Notification::getUserId, userId)
               .eq(Notification::getIsRead, 0);

        long count = notificationMapper.selectCount(wrapper);
        return Map.of("unreadCount", count);
    }

    @Override
    @Transactional
    public void createNotification(Long userId, String title, String content, String type, Long relatedId) {
        Notification notification = new Notification();
        notification.setUserId(userId);
        notification.setTitle(title);
        notification.setContent(content);
        notification.setType(type);
        notification.setRelatedId(relatedId);
        notification.setIsRead(0);
        notificationMapper.insert(notification);
        log.debug("通知已创建: userId={}, title={}", userId, title);
    }

    private NotificationVO convertToVO(Notification notification) {
        return NotificationVO.builder()
                .id(notification.getId())
                .title(notification.getTitle())
                .content(notification.getContent())
                .type(notification.getType())
                .relatedId(notification.getRelatedId())
                .isRead(notification.getIsRead())
                .createTime(notification.getCreateTime())
                .build();
    }

    private Long getCurrentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new BusinessException(401, "未登录");
        }
        return (Long) authentication.getPrincipal();
    }
}
