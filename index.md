---
title: 
layout: withtable
---

This list shows the names of researchers who have been involved with any one of the projects in the database. The `PI` column identifies the projects that they have head the Principal Investigator role on, whereas the `Researcher` column identifies the projects that they have been involved with as a researcher. 

> Search the database for any keyword in any field.


<table class="display">
  <!-- Title,First registered on,RCT_ID,DOI Number,Primary Investigator -->
  {% for row in site.data.summary %}
    {% if forloop.first %}
    <thead>
    <tr>
      <td> RCT ID</td>
    <td> Title </td>
    <td> Primary Investigator </td>
    <td> DOI </td>
    <td> First published</td>
    </tr>
    </thead>
    {% endif %}

  <!-- manually constructing table -->
  <!-- Name,PI,Researcher -->
  <tr>
    <td> <a href="trials/{{ row["RCT_ID_num"] }}.html">{{ row["RCT_ID"] }}</a></td>
    <td> {{ row["Title"] }} </td>
    <td> {{ row["Primary Investigator"] }} </td>
    <td> {{ row["DOI Number"] }} </td>
    <td> {{ row["First registered on"] }} </td>
  </tr>
  {% endfor %}
</table>



To download the entire database, [click here].