package com.smartlegal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartlegal.entity.ComplianceIssue;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import java.util.List;

public interface ComplianceIssueMapper extends BaseMapper<ComplianceIssue> {
    default List<ComplianceIssue> selectByRecordId(Long recordId) {
        return selectList(new LambdaQueryWrapper<ComplianceIssue>().eq(ComplianceIssue::getRecordId, recordId));
    }
}