package com.gukhan.ainlp.user;
import jakarta.persistence.*;
@Entity @Table(name="users") public class User{
@Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
@Column(unique=true,nullable=false) private String username;@Column(nullable=false) private String passwordHash;@Column(nullable=false) private String role;@Column(nullable=false) private boolean active=true;
public User(){} public User(String u,String p,String r){username=u;passwordHash=p;role=r;} public Long getId(){return id;}public String getUsername(){return username;}public String getPasswordHash(){return passwordHash;}public String getRole(){return role;}public boolean isActive(){return active;}public void setActive(boolean a){active=a;}}