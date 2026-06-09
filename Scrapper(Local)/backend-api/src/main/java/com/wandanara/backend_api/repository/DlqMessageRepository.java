package com.wandanara.backend_api.repository;

import com.wandanara.backend_api.entity.DlqMessage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DlqMessageRepository extends JpaRepository<DlqMessage, Long> {
    List<DlqMessage> findTop100ByOrderByFailedAtDesc();
}
