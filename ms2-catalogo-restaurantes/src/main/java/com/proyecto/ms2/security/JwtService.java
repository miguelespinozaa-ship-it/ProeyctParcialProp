package com.proyecto.ms2.security;

import java.nio.charset.StandardCharsets;

import javax.crypto.SecretKey;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

/**
 * Valida los JWT emitidos por MS1 (mismo JWT_SECRET compartido vía env, HS256).
 */
@Component
public class JwtService {

    private final SecretKey key;

    public JwtService(@Value("${JWT_SECRET:change-me-in-prod-use-a-long-random-secret-32-bytes-min}") String secret) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    public Claims parse(String token) throws JwtException {
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
