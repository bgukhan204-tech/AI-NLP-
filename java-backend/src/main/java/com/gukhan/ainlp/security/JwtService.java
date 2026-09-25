package com.gukhan.ainlp.security;
import io.jsonwebtoken.*;import io.jsonwebtoken.security.Keys;import java.nio.charset.StandardCharsets;import java.security.Key;import java.util.Date;import org.springframework.beans.factory.annotation.Value;import org.springframework.stereotype.Service;
@Service public class JwtService{private final Key key;private final long expirationMs;
public JwtService(@Value("${app.jwt.secret}")String secret,@Value("${app.jwt.expiration-ms:900000}")long exp){if(secret==null||secret.length()<32)throw new IllegalArgumentException("JWT secret must contain at least 32 characters");key=Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));expirationMs=exp;}
public String generate(String u,String r){Date n=new Date();return Jwts.builder().subject(u).claim("role",r).issuedAt(n).expiration(new Date(n.getTime()+expirationMs)).signWith(key).compact();}
public String username(String t){return Jwts.parser().verifyWith(key).build().parseSignedClaims(t).getPayload().getSubject();}
public boolean valid(String t){try{Jwts.parser().verifyWith(key).build().parseSignedClaims(t);return true;}catch(JwtException|IllegalArgumentException e){return false;}}}