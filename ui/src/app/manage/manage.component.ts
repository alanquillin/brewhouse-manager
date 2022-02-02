import { Component, OnInit } from '@angular/core';
import { DataService } from './../data.service';
import { Router } from '@angular/router';

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

  goto(path: string): void {
    window.location.href = `/${path}`;
  }
}

