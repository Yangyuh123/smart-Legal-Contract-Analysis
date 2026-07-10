package com.smartlegal.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartlegal.common.PageResult;
import com.smartlegal.common.Result;
import com.smartlegal.service.NotificationService;
import com.smartlegal.vo.NotificationVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 通知控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/notifications")
@RequiredArgsConstructor
@Tag(name = "通知管理", description = "系统通知的查看与已读管理")
public class NotificationController {

    private final NotificationService notificationService;

    @GetMapping
    @Operation(summary = "分页查询通知列表")
    public Result<PageResult<NotificationVO>> list(
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页大小") @RequestParam(defaultValue = "10") int size) {
        Page<NotificationVO> pageResult = notificationService.list(page, size);
        return Result.success(PageResult.of(
                pageResult.getRecords(),
                pageResult.getTotal(),
                pageResult.getCurrent(),
                pageResult.getSize()
        ));
    }

    @GetMapping("/unread-count")
    @Operation(summary = "获取未读通知数量")
    public Result<Map<String, Object>> unreadCount() {
        Map<String, Object> result = notificationService.unreadCount();
        return Result.success(result);
    }

    @PutMapping("/{id}/read")
    @Operation(summary = "标记单条通知为已读")
    public Result<Void> read(@Parameter(description = "通知ID") @PathVariable Long id) {
        notificationService.read(id);
        return Result.success();
    }

    @PutMapping("/read-all")
    @Operation(summary = "标记全部通知为已读")
    public Result<Void> readAll() {
        notificationService.readAll();
        return Result.success();
    }
}
