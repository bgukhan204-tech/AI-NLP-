package com.gukhan.ainlp.document;
import java.util.*;import org.springframework.data.jpa.repository.JpaRepository;
public interface DocumentChunkRepository extends JpaRepository<DocumentChunk,Long>{List<DocumentChunk> findTop8ByDepartmentIn(Collection<String> departments);}