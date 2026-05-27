package com.wandanara.backend_api.repository;

import com.wandanara.backend_api.entity.SearchResult;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SearchResultRepository extends JpaRepository<SearchResult, Long> {

    List<SearchResult> findBySearchId(String searchId);
}