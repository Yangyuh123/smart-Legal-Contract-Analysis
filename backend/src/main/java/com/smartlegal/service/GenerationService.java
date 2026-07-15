package com.smartlegal.service;

import reactor.core.publisher.Flux;
import java.util.Map;

public interface GenerationService {
    Flux<String> streamGenerate(Map<String, Object> request, Long userId);
}
