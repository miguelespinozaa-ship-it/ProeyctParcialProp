package com.proyecto.ms2.controller;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import com.proyecto.ms2.model.Restaurante;
import com.proyecto.ms2.repository.RestauranteRepository;
import com.proyecto.ms2.security.AuthenticatedUser;
import com.proyecto.ms2.security.JwtAuthFilter;

import jakarta.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/api/v1/restaurants")
public class RestaurantController {

    private final RestauranteRepository restauranteRepository;

    public RestaurantController(RestauranteRepository restauranteRepository) {
        this.restauranteRepository = restauranteRepository;
    }

    @GetMapping
    public List<Restaurante> listar(@RequestParam(required = false) String categoria,
                                     @RequestParam(required = false) String ciudad) {
        if (categoria != null) {
            return restauranteRepository.findByCategoria(categoria);
        }
        if (ciudad != null) {
            return restauranteRepository.findByCiudad(ciudad);
        }
        return restauranteRepository.findAll();
    }

    @GetMapping("/{restaurantId}")
    public Restaurante detalle(@PathVariable String restaurantId) {
        return findOrThrow(restaurantId);
    }

    @GetMapping("/{restaurantId}/admin")
    public Restaurante adminView(@PathVariable String restaurantId, HttpServletRequest request) {
        requireOwnerAdmin(request, restaurantId);
        return findOrThrow(restaurantId);
    }

    @PutMapping("/{restaurantId}")
    public Restaurante actualizar(@PathVariable String restaurantId, @RequestBody Restaurante datos, HttpServletRequest request) {
        requireOwnerAdmin(request, restaurantId);
        Restaurante existente = findOrThrow(restaurantId);
        existente.setNombre(datos.getNombre());
        existente.setDireccion(datos.getDireccion());
        existente.setCategoria(datos.getCategoria());
        existente.setCiudad(datos.getCiudad());
        return restauranteRepository.save(existente);
    }

    private Restaurante findOrThrow(String restaurantId) {
        return restauranteRepository.findById(restaurantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Restaurante no encontrado"));
    }

    /** Compartido con MenuController: exige JWT admin cuyo restaurante_id coincida con la ruta. */
    static void requireOwnerAdmin(HttpServletRequest request, String restaurantId) {
        AuthenticatedUser user = (AuthenticatedUser) request.getAttribute(JwtAuthFilter.REQUEST_ATTR);
        if (user == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Falta token de autenticación");
        }
        if (!user.isAdmin() || !restaurantId.equals(user.getRestauranteId())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No autorizado para este restaurante");
        }
    }
}
