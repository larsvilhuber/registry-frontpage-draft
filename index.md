---
title: 
layout: withtable
---

This list shows the names of researchers who have been involved with any one of the projects in the database. The `PI` column identifies the projects that they have head the Principal Investigator role on, whereas the `Researcher` column identifies the projects that they have been involved with as a researcher. 

> Search the database for any keyword in any field.


<table class="display">
  <!-- Proj ID,Status,Title,RDC,Start Year,End Year,PI,Researcher -->
  {% for row in site.data.UniqueResearchers %}
    {% if forloop.first %}
    <thead>
    <tr>
      {% for cell in row %}
        {% if forloop.last %}
        <th>{{ cell[0] }}</th>
          {% continue %}
        {% else %}
        <th>{{ cell[0] }}</th>
        {% endif %}
      {% endfor %}
    </tr>
    </thead>
    {% endif %}

  <!-- manually constructing table -->
  <!-- Name,PI,Researcher -->
  <tr>
    <td> {{ row["Name"] }} </td>
    <td> {{ row["PI"] }} </td>
    <td> {{ row["Researcher"] }} </td>
  </tr>
  {% endfor %}
</table>



To download the entire database, [click here].