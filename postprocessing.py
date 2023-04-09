import asyncio
import csv
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
from tiktokapipy.async_api import AsyncTikTokAPI

# Now using a new TikTok library https://github.com/Russell-Newton/TikTokPy

# Normal GitHub Pages URL
# githubPagesUrl = "https://sparklitwizzl.github.io/tiktok-rss-flat/"

# Custom Domain
githubPagesUrl = "https://tiktokrss.uselesslesbians.gay/"

maxItems = 10
subscriptionFileCount = 5


def log( message ):
	print( f'-------------------- {message} --------------------' )


def logError( exception ):
	log( '!!!!! ERROR !!!!!')
	log( exception )


async def runAll():
	try:
		log( 'runAll start' )
		
		currentFileNumber = 0
		log( 'attempt to load subscription file number to run' )
		with open( 'nextSubscriptionFileToRun.py' ) as f:
			currentFileNumber = f.read()
			log( f'currentFileNumber = {currentFileNumber}' )
		
		fileToRun = 'subscriptions' + currentFileNumber + '.csv'
		log( f'fileToRun = {fileToRun}' )
		
		with open( fileToRun ) as f:
			# TODO: Switch to 3.11 TaskGroup or trio nursery
			await asyncio.gather( *[
				run( row['username'] ) for row in csv.DictReader( f, fieldnames = ['username'] ) ] )
		
		nextFileNumber = int( currentFileNumber ) + 1
		if ( nextFileNumber > subscriptionFileCount ):
			nextFileNumber = 1
		log( f'nextFileNumber = {nextFileNumber}' )
		
		log( f'attempt to store next subscription file number to run ( subscriptions{nextFileNumber}.csv )' )
		with open( 'nextSubscriptionFileToRun.py', 'w' ) as f:
			f.write( str( nextFileNumber ) )
	except Exception as e:
		logError( e )
	
	log( 'runAll end' )


async def run( username ):
	log( f'run start ( {username} )' )
	try:
		feedGenerator = FeedGenerator()
		feedGenerator.id( 'https://tiktok.com/@' + username )
		feedGenerator.title( '@' + username + ' | TikTok' )
		feedGenerator.author( {'name':'Conor ONeill','email':'conor@conoroneill.com'} )
		feedGenerator.link( href = 'http://tiktok.com', rel = 'alternate' )
		feedGenerator.logo( githubPagesUrl + 'tiktok-rss.png' )
		feedGenerator.subtitle( 'Latest TikToks from @' + username )
		feedGenerator.link( href = githubPagesUrl + 'rss/' + username + '.xml', rel = 'self' )
		feedGenerator.language( 'en' )
		
		# Set the last modification time for the feed to be the most recent post, else now.
		updated = None
		
		async with AsyncTikTokAPI( navigation_retries = 3, navigation_timeout = 60 ) as api:
			tiktokUser = await api.username( username, video_limit = maxItems )
			async for video in tiktokUser.videos:
				try:
					# print( video.create_time, video.desc )
					print( "URL = " + "https://tiktok.com/@" + username + "/video/" + str( video.id ) )
					
					feedEntry = feedGenerator.add_entry()
					link = "https://tiktok.com/@" + username + "/video/" + str( video.id )
					feedEntry.id( link )
					
					timestamp = video.create_time
					# print( timestamp )
					feedEntry.published( timestamp )
					feedEntry.updated( timestamp )
					updated = max( timestamp, updated ) if updated else timestamp
					
					if video.desc:
						feedEntry.title( video.desc[0:255] )
					else:
						feedEntry.title( "[no title]" )
					
					feedEntry.link( href = link )
					
					#feedEntry.description( "<img src = '" + tiktok.as_dict['video']['cover'] + "' />" )
					if video.desc:
						feedEntry.description( video.desc )
					else:
						feedEntry.description( "[no description]" )
					
				except Exception as e:
					logError( e )
		
		feedGenerator.updated( updated )
		
		feedFileName = 'rss/' + username + '.xml'
		log( f'attempt to write feed to file {feedFileName}' )
		feedGenerator.atom_file( feedFileName, pretty = True ) # Write the RSS feed to a file
		
	except Exception as e:
		logError( e )
		pass
	
	log( f'run end ( {username} )' )



asyncio.run( runAll() )
