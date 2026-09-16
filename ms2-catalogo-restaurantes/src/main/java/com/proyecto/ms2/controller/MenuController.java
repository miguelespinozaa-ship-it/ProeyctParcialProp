package com.proyecto.ms2.controller;

import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import com.proyecto.ms2.model.Plato;
import com.proyecto.ms2.model.Restaurante;
import com.proyecto.ms2.repository.RestauranteRepository;

import jakarta.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/api/v1/restaurants/{restaurantId}/menu")
public class MenuController {

    private final RestauranteRepository restauranteRepository;

    public MenuController(RestauranteRepository restauranteRepository) {
        this.restauranteRepository = restauranteRepository;
    }

    @GetMapping
    public List<Plato> listar(@PathVariable String restaurantId) {
        return findRestaurante(restaurantId).getPlatos();
    }

    @GetMapping("/{dishId}")
    public Plato detalle(@PathVariable String restaurantId, @PathVariable String dishId) {
        // Usado por MS3 para validar precio/disponibilidad al crear pedido
        return findPlato(findRestaurante(restaurantId), dishId);
    }

    @PostMapping
    public Plato crear(@PathVariable String restaurantId, @RequestBody Plato plato, HttpServletRequest request) {
        RestaurantController.requireOwnerAdmin(request, restaurantId);
        Restaurante restaurante = findRestaurante(restaurantId);
        plato.setId(UUID.randomUUID().toString());
        restaurante.getPlatos().add(plato);
        restauranteRepository.save(restaurante);
        return plato;
    }

    @PutMapping("/{dishId}")
    public Plato editar(@PathVariable String restaurantId, @PathVariable String dishId,
                         @RequestBody Plato datos, HttpServletRequest request) {
        RestaurantController.requireOwnerAdmin(request, restaurantId);
        Restaurante restaurante = findRestaurante(restaurantId);
        Plato plato = findPlato(restaurante, dishId);
        plato.setNombre(datos.getNombre());
        plato.setDescripcion(datos.getDescripcion());
        plato.setPrecio(datos.getPrecio());
        plato.setCategoria(datos.getCategoria());
        plato.setDisponible(datos.isDisponible());
        restauranteRepository.save(restaurante);
        return plato;
    }

    @PatchMapping("/{dishId}/disponibilidad")
    public Plato toggleDisponibilidad(@PathVariable String restaurantId, @PathVariable String dishId,
                                       HttpServletRequest request) {
        RestaurantController.requireOwnerAdmin(request, restaurantId);
        Restaurante restaurante = findRestaurante(restaurantId);
        Plato plato = findPlato(restaurante, dishId);
        plato.setDisponible(!plato.isDisponible());
        restauranteRepository.save(restaurante);
        return plato;
    }

    @DeleteMapping("/{dishId}")
    public void eliminar(@PathVariable String restaurantId, @PathVariable String dishId, HttpServletRequest request) {
        RestaurantController.requireOwnerAdmin(request, restaurantId);
        Restaurante restaurante = findRestaurante(restaurantId);
        Plato plato = findPlato(restaurante, dishId);
        restaurante.getPlatos().remove(plato);
        restauranteRepository.save(restaurante);
    }

    private Restaurante findRestaurante(String restaurantId) {
        return restauranteRepository.findById(restaurantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Restaurante no encontrado"));
    }

    private Plato findPlato(Restaurante restaurante, String dishId) {
        return restaurante.getPlatos().stream()
                .filter(p -> p.getId().equals(dishId))
                .findFirst()
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Plato no encontrado"));
    }
}
