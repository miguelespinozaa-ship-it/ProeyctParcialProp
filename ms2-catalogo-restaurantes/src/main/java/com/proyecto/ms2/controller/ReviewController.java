package com.proyecto.ms2.controller;

import java.time.Instant;
import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import com.proyecto.ms2.model.Resena;
import com.proyecto.ms2.model.Restaurante;
import com.proyecto.ms2.repository.RestauranteRepository;

@RestController
@RequestMapping("/api/v1/restaurants/{restaurantId}/reviews")
public class ReviewController {

    private final RestauranteRepository restauranteRepository;

    public ReviewController(RestauranteRepository restauranteRepository) {
        this.restauranteRepository = restauranteRepository;
    }

    @GetMapping
    public List<Resena> listar(@PathVariable String restaurantId) {
        return findRestaurante(restaurantId).getResenas();
    }

    @PostMapping
    public Resena crear(@PathVariable String restaurantId, @RequestBody Resena resena) {
        if (resena.getPuntuacion() < 1 || resena.getPuntuacion() > 5) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "La puntuación debe estar entre 1 y 5");
        }
        if (resena.getComentario() == null || resena.getComentario().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El comentario es requerido");
        }
        Restaurante restaurante = findRestaurante(restaurantId);
        resena.setFecha(Instant.now());
        restaurante.getResenas().add(resena);
        recalcularCalificacion(restaurante);
        restauranteRepository.save(restaurante);
        return resena;
    }

    private void recalcularCalificacion(Restaurante restaurante) {
        double promedio = restaurante.getResenas().stream()
                .mapToInt(Resena::getPuntuacion)
                .average()
                .orElse(0.0);
        restaurante.setCalificacionPromedio(promedio);
    }

    private Restaurante findRestaurante(String restaurantId) {
        return restauranteRepository.findById(restaurantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Restaurante no encontrado"));
    }
}
