package com.swpu.transflow.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 跨域：前端可能通过 vite 代理、HBuilderX 内置服务器、或独立端口访问本服务，
 * 端口不固定，因此统一放开 /api/** 的跨域。
 * 本项目接口不依赖 Cookie / 会话，放开跨域无安全风险。
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOriginPatterns("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .maxAge(3600);
    }
}
