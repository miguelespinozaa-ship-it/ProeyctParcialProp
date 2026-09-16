package com.proyecto.ms2.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * /health uniforme para los 5 MS (el LB/NGINX pega siempre a la misma ruta).
 * /actuator/health (Spring Boot Actuator) sigue disponible aparte.
 */
@RestController
public class HealthController {

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "ms2-catalogo-restaurantes");
    }
}
