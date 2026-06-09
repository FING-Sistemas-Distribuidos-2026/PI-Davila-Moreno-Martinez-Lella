package com.wandanara.backend_api.controller;

import com.wandanara.backend_api.entity.DlqMessage;
import com.wandanara.backend_api.repository.DlqMessageRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/dlq")
@CrossOrigin(origins = "*")
public class DlqController {

    private final DlqMessageRepository dlqMessageRepository;

    public DlqController(DlqMessageRepository dlqMessageRepository) {
        this.dlqMessageRepository = dlqMessageRepository;
    }

    @GetMapping
    public ResponseEntity<List<DlqMessage>> getDlqMessages() {
        return ResponseEntity.ok(dlqMessageRepository.findTop100ByOrderByFailedAtDesc());
    }
}
