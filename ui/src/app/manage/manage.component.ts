import { Component, OnInit } from '@angular/core';
import { DataService } from './../data.service';
import { Router } from '@angular/router';

//import {  } from './../models/models';

@Component({
  selector: 'manage',
  templateUrl: './manage.component.html',
  styleUrls: ['./manage.component.scss']
})
export class ManageComponent implements OnInit {
  title = 'Manage Brewhouse';

  isLoading = false;

  constructor(private dataService: DataService, private router: Router) {}


  ngOnInit() {  
  }
}

