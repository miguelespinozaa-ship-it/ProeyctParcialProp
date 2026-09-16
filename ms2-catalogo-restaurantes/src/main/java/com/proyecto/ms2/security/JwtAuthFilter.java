package com.proyecto.ms2.security;

import java.io.IOException;

import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/**
 * Extrae y valida el Bearer token en cada request. No rechaza requests sin token:
 * cada controller decide si el endpoint requiere autenticación (ver RestaurantController#requireOwnerAdmin).
 */
@Component
public class JwtAuthFilter extends OncePerRequestFilter {

    public static final String REQUEST_ATTR = "authenticatedUser";

    private final JwtService jwtService;

    public JwtAuthFilter(JwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            try {
                Claims claims = jwtService.parse(header.substring(7));
                Integer userId = Integer.valueOf(claims.getSubject());
                String rol = claims.get("rol", String.class);
                String restauranteId = claims.get("restaurante_id", String.class);
                request.setAttribute(REQUEST_ATTR, new AuthenticatedUser(userId, rol, restauranteId));
            } catch (JwtException | NumberFormatException ex) {
                // token inválido/expirado: se deja sin autenticar, el controller exige 401/403 si aplica
            }
        }
        filterChain.doFilter(request, response);
    }
}
