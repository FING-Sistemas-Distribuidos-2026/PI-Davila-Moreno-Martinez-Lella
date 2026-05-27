package com.wandanara.backend_api.repository;

import com.wandanara.backend_api.entity.Search;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SearchRepository extends JpaRepository<Search, String> {
}