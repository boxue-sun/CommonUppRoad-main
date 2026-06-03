import matplotlib.pyplot as plt

#coord1 = [[-391378,-58806],[3874240, -14780],[3872726, 22494],[-392891,-21530]]
#coord1.append(coord1[0]) #repeat the first point to create a 'closed loop'
#coord2 = [[-392891, -21530], [3872726, 22494], [3872888, 57452], [-392727, 13431]]
#coord2.append(coord2[0]) #repeat the first point to create a 'closed loop'
#coord3 = [[-392727, 13431], [3872888, 57452], [3870684, 92764], [-394931, 48745]]
#coord3.append(coord3[0]) #repeat the first point to create a 'closed loop'

#coord1 = [[-391378,-58806],[-207787, -56914],[-208171, -19625],[-392891,-21530]]
#coord1.append(coord1[0]) #repeat the first point to create a 'closed loop'
#coord2 = [[-392891, -21530], [-208171, -19625], [-208532, 15330], [-392727, 13431]]
#coord2.append(coord2[0]) #repeat the first point to create a 'closed loop'
#coord3 = [[-392727, 13431], [-209847, 15316], [-210211, 50649], [-394931, 48745]]
#coord3.append(coord3[0]) #repeat the first point to create a 'closed loop'

coord1 = [[475195,69426],[477170, 25459],[243636, 14975],[241830,55203]]
coord1.append(coord1[0]) #repeat the first point to create a 'closed loop'
coord2 = [[240565, -25808], [241981, 14901], [482161, 25682], [482819, -22561]]
coord2.append(coord2[0]) #repeat the first point to create a 'closed loop'


coord4 = [[352942, 24186], [356371, 14792], [314100, -638], [310671, 8756]]
coord4.append(coord4[0]) #repeat the first point to create a 'closed loop'

xs1, ys1 = zip(*coord1) #create lists of x and y values
xs2, ys2 = zip(*coord2) #create lists of x and y values
#xs3, ys3 = zip(*coord3) #create lists of x and y values
xs4, ys4 = zip(*coord4) #create lists of x and y values

plt.figure()
plt.plot(333521, 11774,'ro') 
plt.plot(xs1,ys1) 
plt.plot(xs2,ys2) 
#plt.plot(xs3,ys3) 
plt.plot(xs4,ys4) 
plt.show() # if you need...